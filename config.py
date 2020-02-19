class Config(object):
    DEBUG = False
    TESTING = False
    
class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True