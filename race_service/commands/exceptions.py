"""Module for raceplan exceptions."""


class CompetitionFormatNotSupportedException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoRaceclassesInEventException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InconsistentValuesInContestantsException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InconsistentValuesInRaceclassesException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class MissingPropertyException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InvalidDateFormatException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoRaceplanInEventException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class DuplicateRaceplansInEventException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class InconsistentInputDataException(Exception):  # pragma: no cover
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class NoRacesInRaceplanException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CouldNotCreateRaceplanException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class CouldNotCreateRaceException(Exception):
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class IllegalValueInRaceError(Exception):  # pragma: no cover
    """Class representing custom exception for command."""

    def __init__(self, message: str) -> None:
        """Initialize the error."""
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
