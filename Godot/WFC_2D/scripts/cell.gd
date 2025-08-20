extends Node2D

signal collapsed

const CELL_SIZE = 128
const TILE_SCALE_ADJ = 0.9

var tiles : Array
var tile_size : float

onready var tile_scene = preload("res://scenes/Tile.tscn")


func _ready():
	for i in range(16):
		var inst = tile_scene.instance()
		tiles.append(inst)
		inst.frame = i
		inst.connect("clicked", self, "on_Tile_clicked", [inst])
		connect("collapsed", inst, "on_Cell_collapsed")
		add_child(inst)
	tile_size = tiles[0].texture.get_width()
	layout_tiles()


func refresh():
	layout_tiles()
	

func layout_tiles():
	if is_collapsed():
		var collapsed_tile = get_collapsed()
		collapsed_tile.position = Vector2(48,48)
		var end_scale = Vector2(4,4)
		$Tween.interpolate_property(collapsed_tile, "scale", Vector2.ZERO, end_scale, 0.15, Tween.TRANS_CUBIC, Tween.EASE_OUT)
		$Tween.start()
		return
	var i = 0
	for x in range(4):
		for y in range(4):
			var tile = tiles[i]
			if tile:
				tile.position = Vector2(y, x) * (CELL_SIZE / 4.0)
				var t_scale = CELL_SIZE / tile_size
				tile.scale = Vector2(t_scale, t_scale) * TILE_SCALE_ADJ
				i += 1


func constrain(idx):
	var tile = tiles[idx]
	if tile:
		tile.discard()
	tiles[idx] = null
	if is_collapsed():
		emit_signal("collapsed")
	refresh()


func is_collapsed():
	var i = 0
	for t in tiles:
		if t != null:
			i += 1
			if i > 1:
				return false
	if i == 1:
		return true
	else:
		return false


func get_collapsed():
	for t in tiles:
		if t != null:
			return t


func get_tiles():
	var superposition = []
	for i in range(len(tiles)):
		if tiles[i] != null:
			superposition.append(i)
	return superposition


func on_Tile_clicked(tile):
	collapse(tile.frame)

func collapse(idx):
	if idx == -1:
		var possible_tiles = get_tiles()
		var rand_idx = randi() % len(possible_tiles)
		collapse(possible_tiles[rand_idx])
		return
	for i in range(len(tiles)):
		if i == idx:
			continue
		elif tiles[i] == null:
			continue
		else:
			tiles[i].discard()
			tiles[i] = null
	emit_signal("collapsed")
	layout_tiles()
