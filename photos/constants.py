class PhotoStatus:
    PENDING = 0
    APPROVED = 1
    REJECTED = 2


PHOTO_STATUS_CHOICES = (
    (PhotoStatus.PENDING, 'Pending'),
    (PhotoStatus.APPROVED, 'Approved'),
    (PhotoStatus.REJECTED, 'Rejected'),
)
