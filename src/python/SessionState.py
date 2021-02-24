# https://gist.github.com/tvst/036da038ab3e999a64497f42de966a92

"""Hack to add per-session state to Streamlit.
Usage
-----
>>> import SessionState
>>>
>>> session_state = SessionState.get(user_name='', favorite_color='black')
>>> session_state.user_name
''
>>> session_state.user_name = 'Mary'
>>> session_state.favorite_color
'black'
Since you set user_name above, next time your script runs this will be the
result:
>>> session_state = get(user_name='', favorite_color='black')
>>> session_state.user_name
'Mary'
"""

from streamlit.report_thread import get_report_ctx
from streamlit.server.server import Server


class SessionState(object):
    def __init__(self, **kwargs):
        """A new SessionState object.
        Parameters
        ----------
        **kwargs : any
            Default values for the session state.
        Example
        -------
        >>> session_state = SessionState(user_name='', favorite_color='black')
        >>> session_state.user_name = 'Mary'
        ''
        >>> session_state.favorite_color
        'black'
        """
        for key, val in kwargs.items():
            setattr(self, key, val)


def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session


def get(**kwargs):

    this_session = _get_session()

    if not hasattr(this_session, '_custom_session_state'):
        this_session._custom_session_state = SessionState(**kwargs)

    return this_session._custom_session_state
