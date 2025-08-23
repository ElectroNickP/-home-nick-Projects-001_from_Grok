"""
FastAPI application for Telegram Bot Manager.

This module provides the REST API interface using FastAPI framework.
"""

import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..usecases import BotManagementUseCase, ConversationUseCase, SystemUseCase
from .routes import bot_router, conversation_router, system_router

# Security
security = HTTPBearer(auto_error=False)


class APIApp:
    """FastAPI application for Telegram Bot Manager."""

    def __init__(
        self,
        bot_usecase: BotManagementUseCase,
        conversation_usecase: ConversationUseCase,
        system_usecase: SystemUseCase,
        config: dict | None = None,
    ):
        """Initialize FastAPI application with use cases."""
        self.bot_usecase = bot_usecase
        self.conversation_usecase = conversation_usecase
        self.system_usecase = system_usecase
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Create FastAPI app
        self.app = FastAPI(
            title="Telegram Bot Manager API",
            description="REST API for managing Telegram bots, conversations, and system settings",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        self._configure_app()
        self._register_routes()
        self._register_middleware()
        self._register_exception_handlers()

    def _configure_app(self):
        """Configure FastAPI application."""
        # CORS configuration
        cors_origins = self.config.get('cors_origins', ["http://localhost:3000"])
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_routes(self):
        """Register API routes."""
        # Pass use cases to routers
        bot_router.usecase = self.bot_usecase
        conversation_router.usecase = self.conversation_usecase
        system_router.usecase = self.system_usecase

        # Include routers
        self.app.include_router(bot_router, prefix="/api/v1/bots", tags=["bots"])
        self.app.include_router(conversation_router, prefix="/api/v1/conversations", tags=["conversations"])
        self.app.include_router(system_router, prefix="/api/v1/system", tags=["system"])

        # Health check endpoint
        @self.app.get("/health", tags=["health"])
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "telegram-bot-manager"}

        # Root endpoint
        @self.app.get("/", tags=["root"])
        async def root():
            """Root endpoint with API information."""
            return {
                "message": "Telegram Bot Manager API",
                "version": "1.0.0",
                "docs": "/docs",
                "redoc": "/redoc"
            }

    def _register_middleware(self):
        """Register middleware."""
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            """Log all requests."""
            self.logger.info(f"{request.method} {request.url}")
            response = await call_next(request)
            self.logger.info(f"Response status: {response.status_code}")
            return response

    def _register_exception_handlers(self):
        """Register exception handlers."""
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            """Handle HTTP exceptions."""
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code
                }
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            """Handle general exceptions."""
            self.logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "status_code": 500
                }
            )

    async def verify_api_key(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
        """Verify API key for protected endpoints."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # TODO: Implement actual API key verification
        # For now, accept any non-empty token
        if not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return True

    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Run FastAPI application."""
        import uvicorn
        self.logger.info(f"Starting FastAPI app on {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance."""
        return self.app


# Global FastAPI app instance
api_app: APIApp | None = None


def create_app(
    bot_usecase: BotManagementUseCase,
    conversation_usecase: ConversationUseCase,
    system_usecase: SystemUseCase,
    config: dict | None = None,
) -> APIApp:
    """Create FastAPI application instance."""
    global api_app
    api_app = APIApp(bot_usecase, conversation_usecase, system_usecase, config)
    return api_app


def get_app() -> APIApp:
    """Get FastAPI application instance."""
    if api_app is None:
        raise RuntimeError("FastAPI app not initialized. Call create_app() first.")
    return api_app


