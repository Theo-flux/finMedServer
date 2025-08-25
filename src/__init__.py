from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db.main import init_db
from src.features.auth.routers import auth_router
from src.features.budgets.routers import budget_router
from src.features.departments.routers import dept_router
from src.features.expenses.routers import expense_router
from src.features.expenses_category.routers import category_router
from src.features.invoices.routers import invoice_router
from src.features.patients.routers import patients_router
from src.features.payments.routers import payment_router
from src.features.roles.routers import role_router
from src.features.services.routers import service_router
from src.features.users.routers import user_router
from src.utils.exceptions import register_exceptions
from src.utils.middlewares import register_middlewares


@asynccontextmanager
async def life_span(app: FastAPI):
    print("Server started...")
    await init_db()
    yield
    print("Server stopped...")


version = "v1"
api_version = f"/api/{version}"

app = FastAPI(
    swagger="2.0",
    title="finMed – Modern Finance API for Healthcare",
    description="""
        finMed provides a robust FastAPI backend for managing healthcare finance operations.
        From automated billing to secure transactions and reporting, finMed ensures reliable,
        scalable, and efficient handling of sensitive financial data.
    """,
    version=version,
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/mit"},
    contact={"name": "Theo Flux", "email": "tifluse@gmail.com", "url": "https://github.com/Theo-flux/fast-template"},
    docs_url=f"{api_version}/docs",
    openapi_url=f"/api/{version}/openapi.json",
    lifespan=life_span,
)

register_exceptions(app)
register_middlewares(app)

app.include_router(auth_router, prefix=f"{api_version}/auth", tags=["auth"])
app.include_router(user_router, prefix=f"{api_version}/users", tags=["user"])
app.include_router(role_router, prefix=f"{api_version}/roles", tags=["role"])
app.include_router(dept_router, prefix=f"{api_version}/depts", tags=["department"])
app.include_router(service_router, prefix=f"{api_version}/services", tags=["services"])
app.include_router(category_router, prefix=f"{api_version}/categories", tags=["Categories"])
app.include_router(budget_router, prefix=f"{api_version}/budgets", tags=["Budgets"])
app.include_router(expense_router, prefix=f"{api_version}/expenses", tags=["Expenses"])
app.include_router(patients_router, prefix=f"{api_version}/patients", tags=["Patients"])
app.include_router(invoice_router, prefix=f"{api_version}/invoices", tags=["Invoices"])
app.include_router(payment_router, prefix=f"{api_version}/payments", tags=["Payments"])
