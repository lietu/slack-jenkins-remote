import settings
from sjr.utils import setup_logger
from sjr.api import app

setup_logger(app)
app.run(debug=settings.FLASK_DEBUG)
