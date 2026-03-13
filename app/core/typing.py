from pydantic import BaseModel, StrictStr


class AnswerSchema(BaseModel):
    # Question 0
    CN1: StrictStr
    CN2: StrictStr
    # Question 1
    RA: StrictStr | None
    N1: StrictStr
    N2: StrictStr
    # Question 2
    FA: list[StrictStr]
    FN: list[StrictStr]
    # Question 3
    DRA: list[StrictStr]
    DN: list[StrictStr]
    # Question 4
    V: list[StrictStr]
    # Question 5
    EA: list[StrictStr]
    EN: list[StrictStr]
    # Question 6
    EDA: list[StrictStr]
    # Question 7
    MA: list[StrictStr]
    # Question 8
    UCA: list[StrictStr]
    UCN: list[StrictStr]
    # Question 9
    GN1: StrictStr | None
    offering: StrictStr


class DraftSchema(BaseModel):
    # Question 0
    CN1: StrictStr | None
    CN2: StrictStr | None
    # Question 1
    RA: StrictStr | None
    N1: StrictStr | None
    N2: StrictStr | None
    # Question 2
    FA: list[StrictStr] | None
    FN: list[StrictStr] | None
    # Question 3
    DRA: list[StrictStr] | None
    DN: list[StrictStr] | None
    # Question 4
    V: list[StrictStr] | None
    # Question 5
    EA: list[StrictStr] | None
    EN: list[StrictStr] | None
    # Question 6
    EDA: list[StrictStr] | None
    # Question 7
    MA: list[StrictStr] | None
    # Question 8
    UCA: list[StrictStr] | None
    UCN: list[StrictStr] | None
    # Question 9
    GN1: StrictStr | None
    offering: StrictStr | None
