from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db.models.meeting_participant import MeetingParticipant


class ParticipantRepository:
    """Read access to internal meeting-participant relations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def is_participant(self, meeting_id: int, user_id: int) -> bool:
        statement = select(
            exists().where(
                MeetingParticipant.meeting_id == meeting_id,
                MeetingParticipant.user_id == user_id,
            )
        )
        return bool(self.session.scalar(statement))

    def list_by_meeting(self, meeting_id: int) -> list[MeetingParticipant]:
        statement = (
            select(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == meeting_id)
            .order_by(MeetingParticipant.id.asc())
        )
        return list(self.session.scalars(statement))

    def get_participated_meeting_ids(self, user_id: int, meeting_ids: list[int]) -> set[int]:
        """Return internal participant relations in one query for a meeting list."""

        if not meeting_ids:
            return set()
        statement = (
            select(MeetingParticipant.meeting_id)
            .where(
                MeetingParticipant.user_id == user_id,
                MeetingParticipant.meeting_id.in_(meeting_ids),
            )
            .distinct()
        )
        return set(self.session.scalars(statement))
