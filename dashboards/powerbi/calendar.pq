// Create this query as dim_date after loading the fact and forecast queries.
let
    AllDates = List.Transform(List.RemoveNulls(List.Combine({
        fact_sales_transactions[date_key], fact_returns[date_key],
        mart_revenue_forecasts[forecast_date]})), each Date.From(_)),
    StartDate = Date.StartOfYear(List.Min(AllDates)),
    EndDate = Date.EndOfYear(List.Max(AllDates)),
    Dates = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1,0,0,0)),
    Calendar = Table.FromList(Dates, Splitter.SplitByNothing(), {"date_key"}),
    Typed = Table.TransformColumnTypes(Calendar, {{"date_key", type date}}),
    Year = Table.AddColumn(Typed, "year", each Date.Year([date_key]), Int64.Type),
    Month = Table.AddColumn(Year, "month", each Date.Month([date_key]), Int64.Type),
    MonthName = Table.AddColumn(Month, "month_name", each Date.MonthName([date_key], "en-GB"), type text),
    Weekday = Table.AddColumn(MonthName, "weekday", each Date.DayOfWeek([date_key], Day.Monday), Int64.Type)
in Weekday
