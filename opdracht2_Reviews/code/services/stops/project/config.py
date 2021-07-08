import os

class ProductionConfig:
	"""
		Production config.
	"""

	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig:
	"""
		Development config.
	"""

	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

