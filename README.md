# standardlibs
This is a collection of libraries to allow common functionality to be added
to any project.  The majority of these are wrappers which are easier to use
and implement than the underlying libraries.

This project contains the following:

* PGPWrapper : A wrapper that provides encryption of files via PGP/GnuPG.
	This requires PGP/GnuPG to be pre-installed and keys must exist in the
	keychain.
* FTPWrapper : A wrapper that provides easy to use FTP, sFTP, FTPes
	capabilities
* Decorators : This library provides several useful decorators such as
	exponential retry, memoization, and a deprecation warning decorator.
* FileQueue : This library provides file queueing with customizable directory
	locations.
* AESCipher : This library provides string encryption using AES ECB mode.
	This currently uses zero byte padding with plans to add proper padding in
	the future.
* Email : This library provides email capabilities.


There are plans to expand the capabilities of this collection of libraries as
well as the libraries themselves.

**Future changes planned**
#### vX.X.X - (vers number dependent on changes made):
* update AESCipher to use non-zero byte padding
* change Email module to not have empty default emails
* add more tests (Email, PGP, FTP)


---
## Version History
---
_versioning based on [Semantic Versioning 2.0.0](http://semver.org/ "Semantic Versioning 2.0.0")_

#### v0.0.1 - initial project setup - March 12, 2015
* added this README
* added Decorators library and tests
* added AESCipher library and tests
* added FileQueue library and tests
* added FTPWrapper library (no tests yet)
* added PGPWrapper library (no tests yet)
* added Email library (no tests yet)
