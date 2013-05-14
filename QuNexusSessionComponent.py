from _Framework.SessionComponent import SessionComponent


class QuNexusSessionComponent(SessionComponent):
  """ Custom session component for QuNexus that automatically selects first track in red box """

  #def __init__(self, num_tracks = 0, num_scenes = 0, *a, **k)
    #SessionComponent.__init__(self, num_tracks, num_scenes, *a, **k)
  
  def update(self):
    self._reselect_track()
    SessionComponent.update(self)

  def _reselect_track(self):
    tracks_to_use = self.tracks_to_use()
    track = tracks_to_use[self._track_offset] 
    self.song().view.selected_track = track 



