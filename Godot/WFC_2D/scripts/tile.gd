extends Sprite

signal clicked

const DEFAULT_COLOUR = Color.white
const HOVER_COLOUR = Color.red


func discard():
	queue_free()


func _on_Area2D_mouse_entered():
	modulate = HOVER_COLOUR


func _on_Area2D_mouse_exited():
	modulate = DEFAULT_COLOUR


func _on_Area2D_input_event(viewport, event, shape_idx):
	if event.is_action_pressed("lmb"):
		emit_signal("clicked")

	
func on_Cell_collapsed():
	$Area2D.input_pickable = false
	
