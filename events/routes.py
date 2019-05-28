import os
import importlib

from events import views
    

def setup(app):
    app.router.add_get('/ping/', views.ping)
    app.router.add_post('/event/', views.event)
    app.router.add_get('/ws/', views.ws)
