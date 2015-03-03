from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.session import SignedCookieSessionFactory


from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    api_url = settings.get('api_url', 'http://localhost:3333')
    settings['api_url'] = api_url
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_beaker')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('bestgirl', '/best')
    config.add_route('vote', '/__vote')
    config.add_route('contest', '/contest')
    config.add_route('result', '/result/{id}')
    config.add_route('results', '/results')
    config.scan()
    return config.make_wsgi_app()
