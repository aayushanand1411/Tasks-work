import pdfplumber
import fitz

def get_image_coords(pdf_path):
    doc = fitz.open(pdf_path)
    print(f'total pages are {doc.page_count}')
    # print(f'total pages are {len(pdf_path)}')
    new = {}
    for i in range(3, doc.page_count):
        page = doc.load_page(i)
        lst = page.get_bboxlog()
        stroke_paths = []
        for line in lst:
            if line[0] == 'stroke-path':
                stroke_paths.append(line[1])
        if stroke_paths:  # Only add to the dictionary if there are entries
            draw = page.cluster_drawings()
            new[i] = draw
    doc.close()
    return new


image_coords = get_image_coords(r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf" )

doc = pdfplumber.open(r"C:\Users\aayus\Downloads\AD2_SRS_2024_080724.pdf" )
for k,v in image_coords.items():
    page = doc.pages[k]
    for idx,image in enumerate(v):
        img = page.crop(tuple(image)).to_image()
        # print(img,'\n')
        img.save(f'processed_marker_docs/page_{k}_image_{idx}.png')
