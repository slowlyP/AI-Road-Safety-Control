from app.extensions import db


class Detection(db.Model):
    __tablename__ = "detections"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    file_id = db.Column(db.BigInteger, db.ForeignKey("report_files.id"), nullable=False)

    detected_label = db.Column(db.String(100), nullable=False)

    confidence = db.Column(db.Float, nullable=False)

    bbox_x1 = db.Column(db.Integer, nullable=False)
    bbox_y1 = db.Column(db.Integer, nullable=False)
    bbox_x2 = db.Column(db.Integer, nullable=False)
    bbox_y2 = db.Column(db.Integer, nullable=False)

    frame_no = db.Column(db.Integer, nullable=True)
    time_sec = db.Column(db.Float, nullable=True)
    frame_width = db.Column(db.Integer, nullable=True)
    frame_height = db.Column(db.Integer, nullable=True)

    detected_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    @property
    def bbox(self):
        return [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]

    @property
    def label_kor(self):
        # DB에 저장된 영문 클래스 네임을 한글로 매핑
        label_map = {
            "bag": "봉투류",
            "box": "박스형",
            "rock": "낙석",
            "tire": "타이어"
        }
        # 만약 매핑에 없으면 영문 그대로 표시
        return label_map.get(self.detected_label, self.detected_label)

    def to_dict(self):
        return {
            "label": self.detected_label,
            "label_kor": self.label_kor,
            "confidence": self.confidence,
            "bbox": self.bbox,
            "frame_no": self.frame_no,
            "time_sec": self.time_sec,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height
        }