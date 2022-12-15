// Filename: config_http.cxx
// Created by:  drose (15Mar09)
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) Carnegie Mellon University.  All rights reserved.
//
// All use of this software is subject to the terms of the revised BSD
// license.  You should have received a copy of this license along
// with this source code in a file named "LICENSE."
//
////////////////////////////////////////////////////////////////////

#include "config_http.h"
#include "http_connection.h"
#include "http_request.h"
#include "dconfig.h"

Configure(config_http);
NotifyCategoryDef(http, "");

ConfigureFn(config_http) {
  init_libhttp();
}

////////////////////////////////////////////////////////////////////
//     Function: init_libhttp
//  Description: Initializes the library.  This must be called at
//               least once before any of the functions or classes in
//               this library can be used.  Normally it will be
//               called by the static initializers and need not be
//               called explicitly, but special cases exist.
////////////////////////////////////////////////////////////////////
void
init_libhttp() {
  static bool initialized = false;
  if (initialized) {
    return;
  }
  initialized = true;

  HttpConnection::init_type();
  Http_Request::init_type();
}

