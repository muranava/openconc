from setuptools import setup, find_packages

setup(name='openconc',
      version='0.1.1',
      description='A tool for corpus linguists',
      url='https://github.com/magnusnissel/openconc',
      author='Magnus Nissel',
      author_email='magnus@nissel.org',
      license='MIT',
      packages= find_packages(),
      zip_safe=False,
      keywords = ["linguistics", "concordance", "corpus", "nlproc", "nlp"],
      classifiers = [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"]
      )
