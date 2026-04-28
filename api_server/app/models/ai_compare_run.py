from app.extensions import db
from sqlalchemy.sql import func


class AiCompareRun(db.Model):
    __tablename__ = "ai_compare_runs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment="비교분석 실행 ID")

    report_id = db.Column(
        db.BigInteger,
        db.ForeignKey("reports.id"),
        nullable=False,
        index=True,
        comment="원본 신고 ID"
    )

    file_id = db.Column(
        db.BigInteger,
        db.ForeignKey("report_files.id"),
        nullable=False,
        index=True,
        comment="분석 대상 파일 ID"
    )

    requested_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="비교분석 실행 관리자 ID"
    )

    source_type = db.Column(
        db.Enum("이미지", "영상", name="ai_compare_runs_source_type"),
        nullable=False,
        comment="분석 파일 유형"
    )

    compare_mode = db.Column(
        db.Enum("image", "video", name="ai_compare_runs_compare_mode"),
        nullable=False,
        default="video",
        server_default="video",
        comment="비교분석 방식"
    )

    sample_fps = db.Column(
        db.Numeric(4, 2),
        nullable=True,
        comment="영상 비교 샘플링 FPS"
    )

    total_sampled_frames = db.Column(
        db.Integer,
        nullable=True,
        comment="전체 샘플링 프레임 수"
    )

    status = db.Column(
        db.Enum("대기", "진행중", "완료", "실패", name="ai_compare_runs_status"),
        nullable=False,
        default="대기",
        server_default="대기",
        comment="비교분석 실행 상태"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.now(),
        comment="실행 생성 시간"
    )

    started_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="실행 시작 시간"
    )

    finished_at = db.Column(
        db.DateTime,
        nullable=True,
        comment="실행 종료 시간"
    )

    # 관계 설정
    report = db.relationship(
        "Report",
        backref=db.backref("ai_compare_runs", lazy="dynamic")
    )

    file = db.relationship(
        "ReportFile",
        backref=db.backref("ai_compare_runs", lazy="dynamic")
    )

    requester = db.relationship(
        "User",
        foreign_keys=[requested_by],
        backref=db.backref("requested_ai_compare_runs", lazy="dynamic")
    )

    results = db.relationship(
        "AiCompareResult",
        back_populates="compare_run",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return (
            f"<AiCompareRun id={self.id} report_id={self.report_id} "
            f"file_id={self.file_id} compare_mode={self.compare_mode} status={self.status}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "file_id": self.file_id,
            "requested_by": self.requested_by,
            "source_type": self.source_type,
            "compare_mode": self.compare_mode,
            "sample_fps": float(self.sample_fps) if self.sample_fps is not None else None,
            "total_sampled_frames": self.total_sampled_frames,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else None,
            "finished_at": self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else None,
        }