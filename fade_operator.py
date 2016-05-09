bl_info = {
    "name": "Sequencer Fade",
    "description": "Adds Operator to fade audio and opacity of selected strip(s)",
    "author": "Kory Prince <korylprince@gmail.com>",
    "version": (1, 0),
    "category": "Sequencer"
}

import bpy

def log(text):
    print("FadeOperator: " + text)

class FadeOperator(bpy.types.Operator):  
    bl_idname = "sequencer.fade"  
    bl_label = "Fade Strip(s)"
    bl_options = {'REGISTER', 'UNDO'}
    
    length = bpy.props.FloatProperty(name="Seconds", min=0.0, soft_max=10.0, step=100.0, default=3.0)
    cut = bpy.props.BoolProperty(name="Cut strip after fade?", default=True)
    direction = bpy.props.EnumProperty(items=[('FADEIN', 'Fade In', 'Fade in Strip'), ('FADEOUT', 'Fade Out', 'Fade out Strip')], name='Fade Direction', default='FADEOUT')

    # Only show in Sequencer
    @classmethod
    def poll(self, context):
        return isinstance(context.space_data, bpy.types.SpaceSequenceEditor)
  
    def execute(self, context):
        direction = 1.0 if self.direction == 'FADEOUT' else -1.0
        start_frame = context.scene.frame_current
        fps = context.scene.render.fps/context.scene.render.fps_base
        end_frame = int(start_frame + self.length * direction * fps)
        strips = context.selected_sequences
        out_of_range_counter = 0
        for strip in strips:
            log("strip: {0}, strip_start: {1}, strip_end: {2}, start_frame: {3}, end_frame: {4}".format(
                strip.name,
                strip.frame_start,
                strip.frame_final_end,
                start_frame,
                end_frame
                ))
            if (strip.frame_start <= start_frame <= strip.frame_final_end) and (strip.frame_start <= end_frame <= strip.frame_final_end):
                if isinstance(strip, bpy.types.SoundSequence):
                    log("SoundSequence: {0}".format(strip.name))
                    orig = strip.volume
                    strip.keyframe_insert(data_path="volume", frame=start_frame)
                    strip.volume = 0
                    strip.keyframe_insert(data_path="volume", frame=end_frame)
                    strip.volume = orig
                else:
                    log("Other Sequence: {0}".format(strip.name))
                    orig = strip.blend_alpha
                    strip.keyframe_insert(data_path="blend_alpha", frame=start_frame)
                    strip.blend_alpha = 0
                    strip.keyframe_insert(data_path="blend_alpha", frame=end_frame)
                    strip.blend_alpha = orig
            else:
                strip.select = False
                out_of_range_counter += 1

        if len(context.selected_sequences) < 1:
            self.report({'ERROR_INVALID_INPUT'}, 'No selected strips in range!')
            return {'CANCELLED'}
        elif out_of_range_counter > 0:
            self.report({'WARNING'}, '{0} strip(s) out of range'.format(out_of_range_counter))

        if self.cut:
            bpy.ops.sequencer.cut(frame=end_frame, type='HARD', side='LEFT' if self.direction == 'FADEOUT' else 'RIGHT') 

        return {'FINISHED'}
    
    def invoke(self, context, event):
        # fail if no strips are selected
        if len(context.selected_sequences) < 1:
            self.report({'ERROR_INVALID_INPUT'}, 'No strips selected!')
            return {'CANCELLED'}
        # force popup
        return context.window_manager.invoke_props_dialog(self)

    # custom layout for toggle buttons
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "length")
        col.row().prop(self, "direction", expand=True)
        col.prop(self, "cut")

def menu_func(self, context):
    self.layout.operator(FadeOperator.bl_idname)  
  
def register():  
    bpy.utils.register_class(FadeOperator)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)
    
def unregister():
    bpy.utils.unregister_class(FadeOperator)
    bpy.types.SEQUENCER_MT_strip.remove(menu_func)
  
if __name__ == "__main__":  
    register()
