use std::fs::create_dir_all;
use std::fs::OpenOptions;
use std::io::Write;

pub fn print_to_file(content: &str, file_name: &str) {
    let mut path = file_name.to_string();
    let parts: Vec<&str> = path.split('/').collect();
    path = parts.split_last().unwrap().1.join("/");
    create_dir_all(&path).expect("Failed to create directories");
    let mut file = OpenOptions::new()
        .create(true) // Optionally create the file if it doesn't already exist
        .write(true)
        .open(file_name)
        .expect("Unable to open file");

    file.write_all(content.as_bytes())
        .unwrap_or_else(|_| panic!("Failed to write to file {}", &file_name));
}
