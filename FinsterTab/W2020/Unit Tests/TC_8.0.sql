-- Script ID      : TC_8.0 --

SELECT 
      count(distinct instrumentid) instid,
      count(distinct forecastdate) date,
      avg( forecastcloseprice) avgprice
      
FROM dbo_algorithmforecast as a
        left outer join dbo_datedim as d on a.forecastdate = d.date 
       
where forecastdate < current_date()
  and d.isholiday = 0
  and d.weekend = 0
;