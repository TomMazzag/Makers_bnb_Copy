from lib.booking_request_repository import BookingRequestRepository
from lib.booking_manager import BookingManager
from datetime import date

def test_bookings_for_user(db_connection):
    db_connection.seed('seeds/makers_bnb.sql')
    repo = BookingRequestRepository(db_connection)
    bookings = repo.get_bookings_by_user(1)
    print(bookings)
    assert bookings == [
        BookingManager(1, 'Enchanted Retreat', 'user2', date(2024, 5, 10), True, False),
        BookingManager(2, 'Enchanted Retreat', 'user2', date(2024, 5, 11), True, False),
        BookingManager(3, 'Enchanted Retreat', 'user2', date(2024, 5, 12), True, False)
    ]