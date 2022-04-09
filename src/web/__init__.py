"""Web application package."""


from web.app import create_app
from web.posts import catalog, PostID, PostRequest
from web.users import registry
