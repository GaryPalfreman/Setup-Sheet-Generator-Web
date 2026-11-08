import streamlit as st

from setup_sheet import (
    SETUP_FIELDS,
    TOOL_FIELDS,
    blank_setup,
    blank_tool,
    build_filename_prefix,
    export_json,
    encode_image,
    image_bytes,
    generate_pdf_bytes,
    load_json_bytes,
)

st.set_page_config(page_title="Setup Sheet Generator", page_icon="🛠️", layout="wide")

st.markdown(
    """
    <style>
      .block-container {max-width: 1500px; padding-top: 1.25rem;}
      [data-testid="stMetricValue"] {font-size: 1.6rem;}
      .small-note {opacity: .72; font-size: .9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Setup Sheet Generator")
st.caption("Create, edit, preview and download setup sheets directly in your browser.")

if "setup_inputs" not in st.session_state:
    st.session_state.setup_inputs = blank_setup()
if "tools" not in st.session_state:
    st.session_state.tools = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "tool_images" not in st.session_state:
    st.session_state.tool_images = []
if "work_holding_image" not in st.session_state:
    st.session_state.work_holding_image = None

with st.sidebar:
    st.header("Setup Sheet")
    mode = st.radio("Start with", ["New setup sheet", "Edit existing JSON"], horizontal=False)
    logo_file = st.file_uploader("Optional company logo", type=["png", "jpg", "jpeg"])
    st.caption("Created by: Gary Palfreman (fixed)")
    st.caption("The logo is embedded into the generated PDF. Nothing needs to be stored on your Mac.")

if mode == "Edit existing JSON":
    json_file = st.file_uploader("Upload an existing setup-sheet JSON", type=["json"], key="json_loader")
    if json_file and st.button("Load setup sheet", type="primary"):
        try:
            inputs, tools, images, work_image = load_json_bytes(json_file.getvalue())
            st.session_state.setup_inputs = inputs
            st.session_state.tools = tools
            st.session_state.tool_images = images
            st.session_state.work_holding_image = work_image
            st.session_state.edit_index = None
            st.success("Setup sheet loaded.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not load that JSON file: {exc}")

st.subheader("1. Setup details")

with st.form("setup_details_form"):
    col1, col2 = st.columns(2)
    updated = {}
    for idx, field in enumerate(SETUP_FIELDS):
        target = col1 if idx % 2 == 0 else col2
        with target:
            if field == "Comments":
                updated[field] = st.text_area(field, value=st.session_state.setup_inputs.get(field, ""), height=100)
            else:
                updated[field] = st.text_input(field, value=st.session_state.setup_inputs.get(field, ""))
    save_setup = st.form_submit_button("Save setup details", use_container_width=True)

if save_setup:
    st.session_state.setup_inputs = updated
    st.success("Setup details saved.")

st.divider()
st.subheader("2. Tool data")

if st.session_state.tools:
    rows = []
    for i, tool in enumerate(st.session_state.tools, start=1):
        row = {"#": i}
        row.update(tool)
        rows.append(row)
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No tools have been added yet.")

button_cols = st.columns([1, 1, 1, 5])
if button_cols[0].button("Add tool", use_container_width=True):
    st.session_state.edit_index = -1
if button_cols[1].button("Edit tool", use_container_width=True, disabled=not st.session_state.tools):
    st.session_state.edit_index = 0 if st.session_state.tools else None
if button_cols[2].button("Clear all tools", use_container_width=True, disabled=not st.session_state.tools):
    st.session_state.tools = []
    st.session_state.tool_images = []
    st.session_state.edit_index = None
    st.rerun()

if st.session_state.edit_index is not None:
    editing_new = st.session_state.edit_index == -1
    tool_seed = blank_tool() if editing_new else st.session_state.tools[st.session_state.edit_index].copy()

    if not editing_new and st.session_state.tools:
        selected = st.selectbox(
            "Select tool to edit",
            options=list(range(len(st.session_state.tools))),
            format_func=lambda i: f"{i + 1}. {st.session_state.tools[i].get('Tool No + Offset No', '')} — {st.session_state.tools[i].get('Tool Type', '')}",
            index=min(st.session_state.edit_index, len(st.session_state.tools) - 1),
        )
        st.session_state.edit_index = selected
        tool_seed = st.session_state.tools[selected].copy()

    with st.form("tool_editor"):
        tcols = st.columns(3)
        tool_values = {}
        for idx, field in enumerate(TOOL_FIELDS):
            with tcols[idx % 3]:
                tool_values[field] = st.text_input(field, value=tool_seed.get(field, ""), key=f"tool_{field}_{st.session_state.edit_index}")
        fcols = st.columns(3)
        save_tool = fcols[0].form_submit_button("Save tool", use_container_width=True)
        delete_tool = fcols[1].form_submit_button("Delete tool", use_container_width=True, disabled=editing_new)
        cancel_tool = fcols[2].form_submit_button("Cancel", use_container_width=True)

    if save_tool:
        if editing_new:
            st.session_state.tools.append(tool_values)
            st.session_state.tool_images.append(None)
        else:
            st.session_state.tools[st.session_state.edit_index] = tool_values
        st.session_state.edit_index = None
        st.rerun()
    if delete_tool and not editing_new:
        st.session_state.tools.pop(st.session_state.edit_index)
        st.session_state.tool_images.pop(st.session_state.edit_index)
        st.session_state.edit_index = None
        st.rerun()
    if cancel_tool:
        st.session_state.edit_index = None
        st.rerun()

st.divider()
st.subheader("3. Tool Images")
st.caption("Upload up to one image per saved tool. Each image is linked to its tool row and included in the PDF and editable JSON.")

# A dedicated uploader per tool enforces the exact maximum of one image per saved tool.
for index, tool in enumerate(st.session_state.tools):
    title = f"Tool {index + 1} — {tool.get('Tool No + Offset No') or tool.get('Tool Type') or 'Unnamed tool'}"
    with st.expander(title, expanded=False):
        uploaded = st.file_uploader("Tool image (JPG or PNG)", type=["jpg", "jpeg", "png"],
                                    key=f"tool_image_{index}")
        if uploaded is not None:
            try:
                st.session_state.tool_images[index] = encode_image(uploaded.getvalue())
            except Exception as exc:
                st.error(f"Could not process image: {exc}")
        if st.session_state.tool_images[index]:
            st.image(image_bytes(st.session_state.tool_images[index]), width=250)
            if st.button("Remove image", key=f"remove_tool_image_{index}"):
                st.session_state.tool_images[index] = None
                st.rerun()
if not st.session_state.tools:
    st.info("Save a tool in Tool data to enable its image upload.")

st.subheader("4. Work Holding Image")
st.caption("One image for the jaws, fixture, or work holding arrangement.")
holding_upload = st.file_uploader("Work holding image (JPG or PNG)", type=["jpg", "jpeg", "png"],
                                  key="work_holding_upload")
if holding_upload is not None:
    try:
        st.session_state.work_holding_image = encode_image(holding_upload.getvalue())
    except Exception as exc:
        st.error(f"Could not process work holding image: {exc}")
if st.session_state.work_holding_image:
    st.image(image_bytes(st.session_state.work_holding_image), width=300)
    if st.button("Remove work holding image"):
        st.session_state.work_holding_image = None
        st.rerun()

st.divider()
st.subheader("5. Generate files")

inputs = st.session_state.setup_inputs
tools = st.session_state.tools
prefix = build_filename_prefix(inputs)
logo_bytes = logo_file.getvalue() if logo_file else None

m1, m2, m3 = st.columns(3)
m1.metric("Tools", len(tools))
m2.metric("Machine", inputs.get("Machine") or "—")
m3.metric("Program", inputs.get("Program Name") or "—")

required_missing = [name for name in ["Machine", "Program Name", "Drawing No + Revision"] if not inputs.get(name, "").strip()]
if required_missing:
    st.warning("Recommended before generating: " + ", ".join(required_missing))

try:
    pdf_bytes = generate_pdf_bytes(inputs, tools, logo_bytes=logo_bytes,
                                   tool_images=st.session_state.tool_images,
                                   work_holding_image=st.session_state.work_holding_image)
    json_bytes = export_json(inputs, tools, st.session_state.tool_images,
                             st.session_state.work_holding_image)
except Exception as exc:
    st.error(f"Could not generate the setup sheet: {exc}")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "Download setup sheet PDF",
        data=pdf_bytes,
        file_name=f"{prefix}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
with c2:
    st.download_button(
        "Download editable JSON",
        data=json_bytes,
        file_name=f"{prefix}.json",
        mime="application/json",
        use_container_width=True,
    )

with st.expander("Setup sheet data preview"):
    st.json({"user_inputs": inputs, "tool_inputs": tools})

if st.button("Start a new setup sheet"):
    st.session_state.setup_inputs = blank_setup()
    st.session_state.tools = []
    st.session_state.tool_images = []
    st.session_state.work_holding_image = None
    st.session_state.edit_index = None
    st.rerun()

st.markdown(
    '<div class="small-note">Web conversion of the original Tkinter Setup Sheet Generator. PDF and JSON files are generated in memory and downloaded through the browser.</div>',
    unsafe_allow_html=True,
)
