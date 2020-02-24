class Config(object):
    DEBUG = False
    TESTING = False
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
    ARM = '4083140'
    ARM_SENSORS = 8
    WRIST = '4407090'
    WRIST_SENSORS=7
    
class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

