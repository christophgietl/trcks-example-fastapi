"""Do-not-update sentinel for partial update models.

Update models (e.g. `ProductUpdate`) carry either the new attribute value
or the `DO_NOT_UPDATE` sentinel.
Services replace the sentinel with the current attribute value
before they call repository methods.
"""

from typing import Final

DO_NOT_UPDATE: Final = sentinel("DO_NOT_UPDATE")
