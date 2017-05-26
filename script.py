import mdl, os, sys
from display import *
from matrix import *
from draw import *

set_basename = False
basename = 'anim'
set_frames = False
frames = None


"""======== first_pass( commands, symbols ) ==========
  Checks the commands array for any animation commands
  (frames, basename, vary)
  
  Should set num_frames and basename if the frames 
  or basename commands are present
  If vary is found, but frames is not, the entire
  program should exit.
  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.
  jdyrlandweaver
  ==================== """
def first_pass( commands ):
    global frames
    global basename
    global set_frames
    global set_basename

    cmds = [c[0] for c in commands]
    
    if 'vary' in cmds and not 'frames' in cmds:
        print 'Set frames before calling vary!'
        sys.exit()

    for command in commands:
        c = command[0]
        args = command[1:]
        
        if c == 'frames':
            frames = args[0]
            set_frames = True
            
        elif c == 'basename':
            basename = args[0]
            set_basename = True

    if set_frames and not set_basename:
        print 'Default basename set to: ' + basename

    return frames


"""======== second_pass( commands ) ==========
  In order to set the knobs for animation, we need to keep
  a separate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).
  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.
  Go through the command array, and when you find vary, go 
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropriate value. 
  ===================="""

knobs = []

def second_pass( commands, num_frames ):
    global knobs
    global set_frames
    
    if not set_frames:
        return

    knobs = [{} for x in range(num_frames)] 

    for command in commands:
        c = command[0]
        args = command[1:]

        if c == 'vary':

            knob = args[0]
            start_frame  = int(args[1])
            end_frame = int(args[2])
            start_val = float(args[3])
            end_val = float(args[4])

            duration = end_frame - start_frame

            if duration < 0 or start_frame < 0 or end_frame >= frames:
                print 'Invalid frames'
                return

            diff_val = end_val - start_val
            delta = diff_val / duration
            inc = start_val
            m = 1
            
            if delta < 0:
                temp = start_frame
                start_frame = end_frame
                end_frame = temp
                delta *= -1
                m *= -1
                inc = end_val
                end_val = start_val 
                
            for i in range(start_frame, end_frame + m, m):
                knobs[i][knob] = inc
                
                if inc < end_val:
                    inc += delta
                    
    return knobs
                
def run(filename):
    """
    This function runs an mdl script
    """
    global frames
    global set_frames
    global basename
    global set_basename
    global knobs
    
    color = [255, 255, 255]
    tmp = new_matrix()
    ident( tmp )
    screen = new_screen()
    step = 0.01
    
    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print "Parsing failed."
        return

    first_pass(commands)
    second_pass(commands, frames)

    if not set_frames:
        frames = 1
    
    for i in range(frames):
        tmp = new_matrix()
        ident(tmp)
        stack = [ [x[:] for x in tmp] ]
        
        tmp = []
        step = 0.1
        for command in commands:
            #print command
            c = command[0]
            args = command[1:]

            if c == 'set':
                symbols[args[0]][1] = float(args[1]) 

            elif c == 'setknobs':
                for s in symbols:
                    if symbols[s][0] == 'knob':
                        symbols[s][1] = float(args[0])
            
            elif c == 'box':
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'sphere':
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'torus':
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, color)
                tmp = []
            elif c == 'move':
                knob = args[3]

                if knob:
                    x = knobs[i][knob] * args[0]
                    y = knobs[i][knob] * args[1]
                    z = knobs[i][knob] * args[2]
                    args = (x, y, z, knob)
                
                tmp = make_translate(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                knob = args[3]

                if knob:
                    x = knobs[i][knob] * args[0]
                    y = knobs[i][knob] * args[1]
                    z = knobs[i][knob] * args[2]
                    args = (x, y, z, knob)

                tmp = make_scale(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                knob = args[2]

                if knob:
                    theta = knobs[i][knob] * args[1]
                    args = (args[0], theta, knob)
                
                theta = args[1] * (math.pi/180)
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
                
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0])

        name = 'anim/' + basename + (3-len(str(i)))*'0' + str(i) + '.ppm'

        if not os.path.exists('anim'):
            os.makedirs('anim')
        
        save_ppm(screen,name)
        clear_screen(screen)

    make_animation(basename)
