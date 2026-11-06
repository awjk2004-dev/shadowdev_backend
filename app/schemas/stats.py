from pydantic import BaseModel

class StatsResponse(BaseModel):
    body: int
    mind: int
    work: int
    self_development: int # استخدمنا self_development بدلاً من self لأن self كلمة محجوزة
    relations: int
    total_completed: int

class WeeklyStatsResponse(StatsResponse):
    pass

class AllTimeStatsResponse(StatsResponse):
    pass