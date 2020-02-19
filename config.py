class Config(object):
    DEBUG = False
    TESTING = False
    ARM = '4083140'
    ARM_SENSORS = 8
    WRIST = '4407090'
    WRIST_SENSORS=7
    
class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    