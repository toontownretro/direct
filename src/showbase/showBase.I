INLINE CShowBase::CShowBase() {

}

INLINE CShowBase::~CShowBase() {
  stop_collisions_traversal();
  stop_animate_characters();
  //stop_ig_loop();
}

INLINE PT(GraphicsEngine) CShowBase::
get_graphics_engine() {
  if (!graphics_engine) {
    graphics_engine = GraphicsEngine::get_global_ptr();
  }
  return graphics_engine;
}

// Throw the "NewFrame" event in the C++ world.  Some of the lerp code depends
// on receiving this.
INLINE void CShowBase::
throw_new_frame() {
  throw_event("NewFrame");
}