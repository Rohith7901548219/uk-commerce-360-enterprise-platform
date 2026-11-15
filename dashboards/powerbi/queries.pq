// Create text parameters ServerName and DatabaseName in Power BI Desktop.
// Repeat LoadTable("...") for every listed model table; keep credentials in Desktop.
let
    LoadTable = (TableName as text) as table =>
        let
            Source = PostgreSQL.Database(ServerName, DatabaseName, [CreateNavigationProperties=false]),
            Data = Source{[Schema="public", Item=TableName]}[Data],
            Types = if Table.HasColumns(Data, "amount")
                then Table.TransformColumnTypes(Data, {{"amount", Currency.Type}, {"unit_price", Currency.Type}})
                else Data
        in Types
in
    LoadTable
