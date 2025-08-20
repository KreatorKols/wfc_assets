extends Node2D

const W = Vector2.LEFT
const N = Vector2.UP
const E = Vector2.RIGHT
const S = Vector2.DOWN

const CONSTRAINTS = [
[[0,1,2,3,6,7,10,11,15],[1,3],[0,1,2,3,4,7,8,11,15],[4,5,6]], # 0
[[0,1,2,3,6,7,10,11,15],[1,3],[0,1,2,3,4,7,8,11,15],[0,1,2,3,4,5,6,7]], # 1
[[0,1,2,3,6,7,10,11,15],[1,3],[0,1,2,3,4,7,8,11,15],[4,5,6]], # 2
[[0,1,2,3,6,7,10,11,15],[1,3],[0,1,2,3,4,7,8,11,15],[0,1,2,3,4,5,6,7]], # 3
[[0,1,2,3,7,11,15],[0,1,2,3,15],[5,6,12],[8,12]], # 4
[[4,5,14],[0,1,2,3,15],[5,6,12],[9,13]], # 5
[[4,5,14],[0,1,2,3,15],[0,1,2,3,7,11,15],[10,14]], # 6
[[0,1,2,3,6,7,10,11,15],[1,3],[0,1,2,3,4,7,8,11,15],[11,15]], # 7
[[0,1,2,3,7,11,15],[4,8],[9,10,13,14],[8,12]], # 8
[[8,9,12,13],[5,9,12,13,14],[9,10,13,14],[9,13]], # 9
[[8,9,12,13],[6,10],[0,1,2,3,7,11,15],[10,14]], # 10
[[0,1,2,3,6,7,10,11,15],[7,11],[0,1,2,3,4,7,8,11,15],[11,15]], # 11
[[4,5],[4,8],[9,10,13,14],[9,13]], # 12
[[8,9,12,13],[5,9,12,13,14],[9,10,13,14],[9,13]], # 13
[[8,9,12,13],[6,10],[5,6],[9,13]], # 14
[[0,1,2,3,6,7,10,11,15],[7,11],[0,1,2,3,4,7,8,11,15],[4,5,6]] # 15
]

const GRID_SIZE = 6
const GRID_SCALE = 128
const DIRS = [W, N, E, S]

var wavefunction : Array
var stack : Array
var solve_speed = 1.0

onready var cell_scene = preload("res://scenes/Cell.tscn")

func _ready():
	for x in range(GRID_SIZE):
		var row = []
		for y in range(GRID_SIZE):
			var cell = cell_scene.instance()
			var coords = Vector2(x, y)
			row.append(cell)
			cell.position = coords * GRID_SCALE
			cell.connect("collapsed", self, "on_Cell_collapsed", [cell, coords])
			add_child(cell)
		wavefunction.append(row)


func is_fully_collapsed():
	for x in range(GRID_SIZE):
		for y in range(GRID_SIZE):
			var cell = wavefunction[x][y]
			if not cell.is_collapsed():
				return false
	return true


func get_lowest_entropy_coords():
	var lowest_coords = Vector2()
	var lowest_entropy = 0
	for x in range(GRID_SIZE):
		for y in range(GRID_SIZE):
			var cell = wavefunction[x][y]
			var tiles = cell.get_tiles()
			var entropy = len(tiles)
			if entropy <= 1:
				continue
			if not lowest_entropy:
				lowest_entropy = entropy
				lowest_coords = Vector2(x, y)
			elif entropy < lowest_entropy:
				lowest_entropy = entropy
				lowest_coords = Vector2(x, y)
	return lowest_coords
			

func collapse_at_coords(coords):
	wavefunction[coords.x][coords.y].collapse(-1)


func solve():
	solve_speed = 1.0
	while not is_fully_collapsed():
		iterate()


func iterate():
	var coords = get_lowest_entropy_coords()
	collapse_at_coords(coords)
	propagate(coords)


func on_Cell_collapsed(cell, coords):
	get_tree().get_root().set_disable_input(true)
	propagate(coords)

func propagate(coords):
	stack.append(coords)
	while len(stack) > 0:
		var cur_coords = stack.pop_back()
		var cur_cell = wavefunction[cur_coords.x][cur_coords.y]
		var cur_tiles = cur_cell.get_tiles()
		
		for d in DIRS:
			var other_coords = cur_coords + d
			if not is_valid_direction(other_coords):
				continue
			var other_cell = wavefunction[other_coords.x][other_coords.y]
			var other_tiles = other_cell.get_tiles()
			
			var possible_neighbours = get_all_possible_neighbours(d, cur_tiles)
			
			for tile in other_tiles:
				if not tile in possible_neighbours:
					other_cell.constrain(tile)
					
					if solve_speed < 1.0:
						yield(get_tree(), "idle_frame")
						var test = 1.0
						for i in range(int((1.0 - solve_speed) * 1000000)):
							test += 1.0
						
					if not other_coords in stack:
						stack.append(other_coords)
	get_tree().get_root().set_disable_input(false)	
	


func get_all_possible_neighbours(dir, tiles):
	var possibilities = []
	var dir_idx = DIRS.find(dir)
	for tile in tiles:
		possibilities += CONSTRAINTS[tile][dir_idx]
	return possibilities


func is_valid_direction(dir):
	if dir.x < 0:
		return false
	elif dir.x > GRID_SIZE - 1:
		return false
	elif dir.y < 0:
		return false
	elif dir.y > GRID_SIZE - 1:
		return false
	else:
		return true


func _on_InteractiveUI_speed_changed(value):
	solve_speed = value


func _on_InteractiveUI_solve():
	solve()
