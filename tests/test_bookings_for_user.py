from lib.booking_request_repository import BookingRequestRepository
from lib.booking_manager import BookingManager
from lib.booking_request import BookingRequest

def test_bookings_for_user(db_connection):
    db_connection.seed('seeds/makers_bnb.sql')
    repo = BookingRequestRepository(db_connection)
    repo.get_bookings_by_user(1)
    assert 1 == 2