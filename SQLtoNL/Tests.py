from SQLtoNL import SQLtoNL
import MRPGraphTranslator

query1 = 'SELECT * from table1, table2 where table1.id = 1 and table1.col1 = ' \
         'table2.col1 '

query2 = """SELECT Orders.OrderID, Customers.CustomerName, Orders.OrderDate
            FROM Orders
            INNER JOIN Customers ON Orders.CustomerID=Customers.CustomerID"""

query3 = """select students.name, students.GPA, comments.text, instructors.name
from 
students, comments,
studenthistory, courses, departments,
coursesched, instructors,
where
students.suid = comments.suid and
students.suid = studenthistory.suid and studenthistory.courseid = courses.courseid and
courses.depid = departments.depid and
courses.courseid = coursesched.courseid and coursesched.instrid = instructors.instrid and
students.class = 2011 and comments.rating > 3 and
coursesched.term = 'spring' and departments.name = 'CS'"""

query4 = """select studenthistory.year, studenthistory.term, max(studenthistory.grade)
from studenthistory
group by
studenthistory.year, studenthistory.term having avg(studenthistory.grade) > 3"""

geo_query_1 = """SELECT state.capital FROM state, border_info WHERE border_info.border=state.state_name AND 
border_info.state_name='texas'; """

geo_query_2 = """SELECT river.river_name FROM river WHERE river.test = 'TEST';"""

nested_query_1 = """SELECT river.traverse FROM river WHERE river.length=(SELECT max(river.length) FROM river);"""

# what is the longest river in the smallest state in the usa
nested_query_2 = """SELECT river.river_name FROM river 
WHERE river.traverse 
IN(SELECT state.state_name FROM state WHERE state.area=(SELECT min(state.area) FROM state)) 
AND river.length=(SELECT max(river.length) FROM river WHERE river.traverse IN(SELECT state.state_name FROM state WHERE state.area=(SELECT min(state.area) FROM state)));"""

# what state borders the least states excluding alaska and excluding hawaii
complex_query = """SELECT state.state_name FROM state 
left outer join border_info ON state.state_name = border_info.state_name 
WHERE state.state_name <> 'alaska' 
AND state.state_name <> 'hawaii' 
GROUP BY state.state_name having count(border_info.border) = 
(SELECT min(cnt) FROM (SELECT state.state_name, count(border_info.border) AS cnt FROM state left outer join border_info 
ON state.state_name = border_info.state_name WHERE state.state_name <> 'alaska' AND state.state_name <> 'hawaii' 
GROUP BY state.state_name) tmp);"""

any_query = """SELECT Products.ProductName
FROM Products
WHERE Products.ProductID = ALL (SELECT OrderDetails.ProductID FROM OrderDetails WHERE OrderDetails.Quantity = 10);"""

s = SQLtoNL(MRPGraphTranslator.MRPGraphTranslator())
print(s.translate(query3))
s.write_to_dot("test.dot")
