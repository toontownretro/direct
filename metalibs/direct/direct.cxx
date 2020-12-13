// This is the one file in this directory which is actually compiled.  It
// exists just so we can have some symbols and make the compiler happy.

#if defined(_WIN32) && !defined(CPPPARSER) && !defined(LINK_ALL_STATIC)
__declspec(dllexport)
#endif
int direct;
