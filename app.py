import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, g
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

load_dotenv()

from src.config import settings
from src.extensions import init_extensions
from src.database import db_manager
from src.logger_config import setup_logging, RequestLogger
from src.services import document_service, query_service
from src.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    QueryRequest,
    QueryResponse,
    ErrorResponse,
    HealthCheckResponse,
    DocumentDeleteResponse,
    StatsResponse,
)
from src.exceptions import (
    RAGLeoException,
    DocumentNotFoundError,
    ValidationError,
    FileUploadError,
)
from src.utils import ensure_dirs, get_directory_size

setup_logging()
logger = logging.getLogger(__name__)

APP_START_TIME = time.time()

def create_app(config_override=None) -> Flask:
    app = Flask(__name__)

    app.config.from_object(settings)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_CONTENT_LENGTH

    if config_override:
        app.config.update(config_override)

    ensure_dirs()

    init_extensions(app)

    with app.app_context():
        db_manager.create_tables()

    request_logger = RequestLogger(app)

    register_error_handlers(app)

    register_routes(app)

    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = (time.time() - g.start_time) * 1000
            response.headers['X-Response-Time'] = f"{elapsed:.2f}ms"
        return response

    logger.info(f"Application initialized - Environment: {settings.ENV}")
    return app

def register_error_handlers(app: Flask):

    @app.errorhandler(RAGLeoException)
    def handle_app_exception(error):
        logger.error(f"{error.error_type}: {error.message}", exc_info=True)
        response = ErrorResponse(
            error=error.message,
            error_type=error.error_type,
            details=error.details
        )
        return jsonify(response.model_dump()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        logger.warning(f"HTTP {error.code}: {error.description}")
        response = ErrorResponse(
            error=error.description or "HTTP error",
            error_type=f"http_{error.code}"
        )
        return jsonify(response.model_dump()), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        response = ErrorResponse(
            error="An internal server error occurred",
            error_type="internal_server_error"
        )
        return jsonify(response.model_dump()), 500

    @app.errorhandler(413)
    def handle_file_too_large(error):
        max_mb = settings.MAX_CONTENT_LENGTH / (1024 * 1024)
        response = ErrorResponse(
            error=f"File too large. Maximum size is {max_mb:.1f}MB",
            error_type="file_too_large"
        )
        return jsonify(response.model_dump()), 413

def register_routes(app: Flask):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/admin')
    def admin():
        return render_template('admin.html')

    @app.route('/api/v1/documents', methods=['GET'])
    def list_documents():
        try:
            documents = document_service.list_documents()

            total_size = sum(doc.file_size for doc in documents)

            response = DocumentListResponse(
                documents=[doc.to_dict() for doc in documents],
                count=len(documents),
                total_size_bytes=total_size
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error listing documents: {e}", exc_info=True)
            raise

    @app.route('/api/v1/upload', methods=['POST'])
    def upload():
        try:
            if 'file' not in request.files:
                raise FileUploadError('No file part in request')

            file = request.files['file']
            if file.filename == '':
                raise FileUploadError('No file selected')

            document, stats = document_service.upload_document(file)

            response = DocumentUploadResponse(
                message='Document uploaded and indexed successfully',
                doc_id=document.doc_id,
                filename=document.original_filename,
                chunks_count=stats['chunks_count'],
                text_length=stats['text_length'],
                file_size=stats['file_size'],
                processing_time_seconds=stats['processing_time_seconds']
            )

            return jsonify(response.model_dump()), 201

        except RAGLeoException:
            raise
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            raise FileUploadError(f"Upload failed: {str(e)}")

    @app.route('/api/v1/ask', methods=['POST'])
    def ask():
        try:
            data = request.get_json() or {}

            try:
                query_req = QueryRequest(**data)
            except Exception as e:
                raise ValidationError(f"Invalid request data: {str(e)}")

            query_record, response_data = query_service.execute_query(
                doc_id=query_req.doc_id,
                query_text=query_req.query,
                top_k=query_req.top_k,
                temperature=query_req.temperature,
                max_tokens=query_req.max_tokens
            )

            response = QueryResponse(**response_data)
            return jsonify(response.model_dump()), 200

        except RAGLeoException:
            raise
        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            raise ValidationError(f"Query failed: {str(e)}")

    @app.route('/api/v1/document/<doc_id>', methods=['DELETE'])
    def delete_document(doc_id):
        try:
            document = document_service.delete_document(doc_id)

            response = DocumentDeleteResponse(
                message='Document deleted successfully',
                doc_id=document.doc_id,
                filename=document.original_filename,
                deleted_at=datetime.utcnow()
            )

            return jsonify(response.model_dump()), 200

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Delete error: {e}", exc_info=True)
            raise ValidationError(f"Deletion failed: {str(e)}")

    @app.route('/api/v1/health', methods=['GET'])
    def health():
        try:
            uptime = time.time() - APP_START_TIME

            with db_manager.get_session() as session:
                doc_count = db_manager.get_document_count(session)
                query_count = db_manager.get_query_count(session)
                db_status = "healthy"

            pipeline_status = "healthy" if document_service.pipeline else "unavailable"

            disk_usage = 0
            for folder in [settings.get_upload_path(), settings.get_index_path()]:
                if folder.exists():
                    disk_usage += get_directory_size(folder)
            disk_usage_mb = disk_usage / (1024 * 1024)

            response = HealthCheckResponse(
                status="healthy",
                app_name=settings.APP_NAME,
                version=settings.APP_VERSION,
                environment=settings.ENV,
                timestamp=datetime.utcnow(),
                uptime_seconds=round(uptime, 2),
                documents_count=doc_count,
                queries_count=query_count,
                database_status=db_status,
                pipeline_status=pipeline_status,
                disk_usage_mb=round(disk_usage_mb, 2)
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/api/v1/stats', methods=['GET'])
    def stats():
        try:
            uptime = time.time() - APP_START_TIME

            with db_manager.get_session() as session:
                from sqlalchemy import func, select
                from src.models import Document, Query

                total_docs = db_manager.get_document_count(session)
                total_queries = db_manager.get_query_count(session)
                active_docs = db_manager.get_document_count(session, include_deleted=False)

                avg_processing_stmt = select(func.avg(Document.processing_time_seconds)).where(
                    Document.processing_time_seconds.isnot(None)
                )
                avg_processing = session.execute(avg_processing_stmt).scalar() or 0

                avg_query_stmt = select(func.avg(Query.total_time_ms)).where(
                    Query.total_time_ms.isnot(None)
                )
                avg_query = session.execute(avg_query_stmt).scalar() or 0

                total_chunks_stmt = select(func.sum(Document.chunks_count)).where(
                    Document.chunks_count.isnot(None)
                )
                total_chunks = session.execute(total_chunks_stmt).scalar() or 0

            storage_used = 0
            for folder in [settings.get_upload_path(), settings.get_index_path(), settings.get_metadata_path()]:
                if folder.exists():
                    storage_used += get_directory_size(folder)
            storage_mb = storage_used / (1024 * 1024)

            response = StatsResponse(
                total_documents=total_docs,
                total_queries=total_queries,
                total_chunks=total_chunks,
                active_documents=active_docs,
                average_processing_time_seconds=round(avg_processing, 2),
                average_query_time_ms=round(avg_query, 2),
                storage_used_mb=round(storage_mb, 2),
                uptime_seconds=round(uptime, 2)
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Stats error: {e}", exc_info=True)
            raise ValidationError(f"Stats retrieval failed: {str(e)}")

app = create_app()

if __name__ == '__main__':
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )
