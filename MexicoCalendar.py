from QuantLib import *

class MexicoCalendar(UnitedStates):
    def __init__(self):
        # Call the constructor of the UnitedStates calendar
        # You might want to call with 'GovernmentBond' to ensure a default calendar is initiated
        UnitedStates.__init__(self, UnitedStates.GovernmentBond)

    # Override the method to add or remove holidays specific for Mexico
    def isBusinessDay(self, date):
        weekDay = date.weekday()
        
        if weekDay == Saturday or weekDay == Sunday:
            return False

        # New Year's Day (example)
        if date.dayOfMonth() == 1 and date.month() == January:
            return False
        # Add other holidays specific to the Mexican market...

        # Check if it's a holiday in the United States calendar
        if super(MexicoCalendar, self).isHoliday(date):
            return False

        return True

    # No need to override isWeekend, as it's properly defined in the parent class
