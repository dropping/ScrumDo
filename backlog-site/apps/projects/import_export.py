from django.http import HttpResponse
import StringIO
import xlrd
import xlwt
from xml.dom.minidom import Document
import csv

from projects.models import Story

ezxf = xlwt.easyxf

def export_iteration(iteration, format ):
  
  if format == "xls":
    return export_excel( iteration )
  elif format == "xml":
    return export_xml( iteration )
  else:
    return export_csv( iteration )

    
def get_headers( project ):
  wrap_xf = ezxf('align: wrap on, vert top')
  numeric_xf = ezxf('align: wrap on, vert top, horiz right')
  return [ (50,"Story ID", lambda story: story.local_id ,numeric_xf),
           (350,"Summary", lambda story: story.summary,wrap_xf),
           (300,"Detail", lambda story: story.detail ,wrap_xf),
           (50,"Points", lambda story: int(story.points) if story.points.isdigit() else story.points, numeric_xf),
           (70,"Status", lambda story: Story.STATUS_CHOICES[story.status-1][1] ,wrap_xf),
           (70,"Assignee", lambda story:  story.assignee.username if story.assignee is not None else "" ,wrap_xf),
           (50,"Rank", lambda story: story.rank,numeric_xf ),          
           (200,project.extra_1_label, lambda story: story.extra_1,wrap_xf), 
           (200,project.extra_2_label, lambda story: story.extra_2,wrap_xf), 
           (200,project.extra_3_label, lambda story: story.extra_3,wrap_xf)
         ]
          
def export_excel( iteration ):
  response = HttpResponse( mimetype="Application/vnd.ms-excel")
  response['Content-Disposition'] = 'attachment; filename=iteration.xls'
  stories = iteration.stories.all().order_by("rank")
  w = xlwt.Workbook()
  ws = w.add_sheet('Iteration Export')
  
  headers = get_headers(iteration.project)
  heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center')  
  for idx,header in enumerate(headers):
    ws.write(0,idx,header[1],heading_xf)
    ws.col(idx).width = 37*header[0]

  for idx, story in enumerate(stories):
    for hidx, header in enumerate(headers):
      f = header[2]
      ws.write(1+idx,hidx, f(story), header[3] )


  w.save(response)
  return response
  


def export_xml( iteration ):
  stories = iteration.stories.all().order_by("rank")
  doc = Document()  
  iteration_node = doc.createElement("iteration")
  doc.appendChild(iteration_node)

  headers = get_headers(iteration.project)  
  
  for idx, story in enumerate(stories):
    row = []
    story_node = doc.createElement("story")
    iteration_node.appendChild( story_node )
    for hidx, header in enumerate(headers):
      f = header[2]
      story_node.setAttribute(to_xml_node_name(header[1]), str(f(story)).replace("\n"," ").replace("\r",""))
      # TODO: There's a bug in the minidom implementation that doesn't convert newlines to their entities, and there's
      #       no good work-around I can find without monkey patching minidom


  response = HttpResponse(doc.toprettyxml(indent="  "), mimetype="text/xml") 
  response['Content-Disposition'] = 'attachment; filename=iteration.xml'
  return response
  
def to_xml_node_name( name ):
  return name.replace(" ","_").lower()

def export_csv( iteration ):
  response =  HttpResponse( mimetype="text/csv") 
  response['Content-Disposition'] = 'attachment; filename=iteration.csv'
  stories = iteration.stories.all().order_by("rank")

  writer = csv.writer(response, delimiter=',' ,  quoting=csv.QUOTE_ALL, escapechar='\\')
    
  headers = get_headers(iteration.project)  
  row = []
  for idx,header in enumerate(headers):
    row.append(header[1])
  
  writer.writerow( row )
  
  for idx, story in enumerate(stories):
    row = []
    for hidx, header in enumerate(headers):
      f = header[2]
      row.append( f(story) )
    writer.writerow( row )

  return response
  
