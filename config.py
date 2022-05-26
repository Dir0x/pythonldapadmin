import os

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or '5aBniNA&NR#b1a6gLnl!!L0j8GXm.A#CP1t4ccWpTq@8cureeB'
