from __future__ import print_function
import json

seatmap = json.load(open('seatmap.json', 'r'))

# Structure is:
# floors: {
#   $floor_id: {
#     name: "Hall D"
# We call them halls instead though
hall_id_map = {k: v['name'] for k,v in list(seatmap['floors'].items())}
# Structure is:
# rows: {
#   $floor_id: {
#     $row_id: {
#       name: "B20"
# Row IDs are unique, so we ignore which floor they belong to
row_id_map = {k: v['name'] for x in list(seatmap['rows'].values()) for k, v in list(x.items())}
# Structure is:
# seat_types: {
#   $seat_type_id: {
#     width: X
#     height: Y
seat_type_map = seatmap['seat_types']

# Structure is:
# seats: {
#   $floor_id: {
#     $seat_id: {
#       name: "20"
#       row_id: $row_id
#       floor_id: $floor_id
#       seat_type_id: $seat_type_id

# Since floor_id is redundant we use the one inside the seat object.
seats = (v for x in list(seatmap['seats'].values()) for v in list(x.values()))

output = []
for seat in seats:
  row = row_id_map[seat['row_id']]
  hall = hall_id_map[seat['floor_id']]
  seat_type = seat_type_map[seat['seat_type_id']]
  seat_idx = seat['name']
  x1 = seat['x']
  y1 = seat['y']
  x2 = seat['x'] + seat_type['width']
  y2 = seat['y'] + seat_type['height']
  output.append({
      'x1': x1,
      'y1': y1,
      'x2': x2,
      'y2': y2,
      'seat': seat_idx,
      'hall': hall,
      'row': row,
    })

print(json.dumps(output, indent=4))
