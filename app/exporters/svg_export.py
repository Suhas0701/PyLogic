from app.ui.canvas.routing import OrthogonalRouter

def export_to_svg(renderer, width=3000, height=2000) -> str:
    # A massive 3000x2000 canvas to ensure all components fit
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-500 -500 {width} {height}" style="background-color: #1e1e1e;">']
    
    # 1. Draw Wires (Underneath Gates)
    for uw in renderer.ui_wires:
        state = getattr(uw.backend_source_pin, 'state', 0)
        bus_width = getattr(uw.backend_source_pin, 'bit_width', 1)
        
        # Match Flet Colors: GREEN_400 (Active) vs GREEN_900 (Inactive)
        stroke = "#4ade80" if state > 0 else "#14532d"  
        stroke_width = max(2, 3 + bus_width)
        
        path_points = OrthogonalRouter.route(uw.source_pin.global_pos, uw.target_pin.global_pos)
        if not path_points: continue
        
        # Build standard SVG path syntax (Move to, Line to)
        d = f"M {path_points[0].x} {path_points[0].y}"
        for p in path_points[1:]:
            d += f" L {p.x} {p.y}"
            
        svg.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{stroke_width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

    # 2. Draw Gates (On top of Wires)
    for gate in renderer.ui_gates.values():
        x = gate.world_pos.x
        y = gate.world_pos.y
        w = gate.width
        h = gate.height
        
        # Match Flet Backgrounds
        fill = "#37474F" # BLUE_GREY_800
        if gate.label in ["SWITCH", "CLOCK"]:
            state_obj = getattr(gate.backend_comp, "_state", 0)
            fill = "#43A047" if state_obj > 0 else "#B71C1C" # GREEN_600 vs RED_900
        elif gate.label == "LED":
            is_lit = getattr(gate.backend_comp, "is_lit", False)
            fill = "#EF5350" if is_lit else "#263238" # RED_400 vs BLUE_GREY_900
            
        # Draw Gate Body
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="transparent"/>')
        
        # Draw Component Label (Center aligned)
        svg.append(f'<text x="{x + w/2}" y="{y + h/2 + 5}" fill="white" font-family="sans-serif" font-weight="bold" font-size="14" text-anchor="middle">{gate.label}</text>')
        
        # 3. Draw Pins
        for pin in gate.pins:
            px = pin.global_pos.x
            py = pin.global_pos.y
            pin_fill = "#90CAF9" if pin.is_input else "#A5D6A7" # BLUE_200 vs GREEN_200
            svg.append(f'<circle cx="{px}" cy="{py}" r="{pin.radius}" fill="{pin_fill}"/>')
            
            # Draw Pin Names inside the gate
            align = "start" if pin.is_input else "end"
            text_x = px + 10 if pin.is_input else px - 10
            svg.append(f'<text x="{text_x}" y="{py + 3}" fill="#ffffff" fill-opacity="0.54" font-family="sans-serif" font-size="10" font-weight="600" text-anchor="{align}">{pin.pin_id}</text>')

    svg.append('</svg>')
    return "\n".join(svg)