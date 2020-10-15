#define OTHER_LIBS \
    express:c pandaexpress:m \
    pstatclient:c pipeline:c panda:m \
    interrogatedb  \
    dtoolutil:c dtoolbase:c dtool:m prc pandabase:c \
    downloader:c $[if $[HAVE_NET],net:c] $[if $[WANT_NATIVE_NET],nativenet:c] \
    linmath:c putil:c

#define LOCAL_LIBS \
    directbase
#define YACC_PREFIX dcyy
#define C++FLAGS -DWITHIN_PANDA
#define UNIX_SYS_LIBS m

#begin lib_target
  #define TARGET dcparser

  #define BUILDING_DLL BUILDING_DIRECT_DCPARSER

  #define SOURCES \
    dcAtomicField.h dcAtomicField.I \
    dcClass.h dcClass.I \
    dcDeclaration.h \
    dcField.h dcField.I \
    dcFile.h dcFile.I \
    dcKeyword.h dcKeywordList.h \
    dcLexerDefs.h \
    dcMolecularField.h \
    dcParserDefs.h \
    dcSubatomicType.h \
    dcPackData.h dcPackData.I \
    dcPacker.h dcPacker.I \
    dcPackerCatalog.h dcPackerCatalog.I \
    dcPackerInterface.h dcPackerInterface.I \
    dcParameter.h \
    dcClassParameter.h \
    dcArrayParameter.h \
    dcSimpleParameter.h \
    dcSwitchParameter.h \
    dcNumericRange.h dcNumericRange.I \
    dcSwitch.h \
    dcTypedef.h \
    dcbase.h \
    dcindent.h \
    dcmsgtypes.h \
    hashGenerator.h \
    primeNumberGenerator.h \
    dcParser.yxx dcLexer.lxx

  #define COMPOSITE_SOURCES \
    dcAtomicField.cxx \
    dcClass.cxx \
    dcDeclaration.cxx \
    dcField.cxx \
    dcFile.cxx \
    dcKeyword.cxx \
    dcKeywordList.cxx \
    dcMolecularField.cxx \
    dcSubatomicType.cxx \
    dcPackData.cxx \
    dcPacker.cxx \
    dcPackerCatalog.cxx \
    dcPackerInterface.cxx \
    dcParameter.cxx \
    dcClassParameter.cxx \
    dcArrayParameter.cxx \
    dcSimpleParameter.cxx \
    dcSwitchParameter.cxx \
    dcSwitch.cxx \
    dcTypedef.cxx \
    dcindent.cxx \
    hashGenerator.cxx \
    primeNumberGenerator.cxx

  #define IGATESCAN all

  #define IGATEEXT \
    dcClass_ext.cxx dcClass_ext.h \
    dcField_ext.cxx dcField_ext.h \
    dcPacker_ext.cxx dcPacker_ext.h

  #define INSTALL_HEADERS \
    dcAtomicField.h dcAtomicField.I \
    dcClass.h dcClass.I \
    dcDeclaration.h \
    dcField.h dcField.I \
    dcFile.h dcFile.I \
    dcKeyword.h dcKeywordList.h \
    dcLexerDefs.h \
    dcMolecularField.h \
    dcParserDefs.h \
    dcSubatomicType.h \
    dcPackData.h dcPackData.I \
    dcPacker.h dcPacker.I \
    dcPackerCatalog.h dcPackerCatalog.I \
    dcPackerInterface.h dcPackerInterface.I \
    dcParameter.h \
    dcClassParameter.h \
    dcArrayParameter.h \
    dcSimpleParameter.h \
    dcSwitchParameter.h \
    dcNumericRange.h dcNumericRange.I \
    dcSwitch.h \
    dcTypedef.h \
    dcbase.h \
    dcindent.h \
    dcmsgtypes.h \
    hashGenerator.h \
    primeNumberGenerator.h

#end lib_target
