class Config(object):
    NAME = 'exoskelebox'
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-should-be-changed'
    BIOX_DEVICES = {
        'arm': {
            'serial_number': '4083140',
            'sensors': 8
        },
        'wrist': {
            'serial_number': '4407090',
            'sensors': 7
        }
    }
    
class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    