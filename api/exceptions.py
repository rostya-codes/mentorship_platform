class SlotDoesNotExist(Exception):
    pass


class ReviewAlreadyExists(Exception):
    pass


class NotYourSlot(Exception):
    pass


class CannotLeaveBefore(Exception):
    pass


class TooSmallStars(Exception):
    pass


class TooBigComment(Exception):
    pass


class EditDeleteExpired(Exception):
    pass
