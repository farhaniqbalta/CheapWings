use std::process::Command;

fn main() {
    for path in [
        "../Cargo.toml",
        "../Cargo.lock",
        "../source-revision.sh",
        "../cheapwings-core",
        "../cheapwings-py",
        "../cheapwings-ffi",
        "../cheapwings-store",
    ] {
        println!("cargo:rerun-if-changed={path}");
    }
    let output = Command::new("sh")
        .arg("../source-revision.sh")
        .output()
        .expect("run core revision script");
    assert!(output.status.success(), "core revision script failed");
    let revision = std::str::from_utf8(&output.stdout).expect("UTF-8 revision");
    println!(
        "cargo:rustc-env=CHEAPWINGS_CORE_REVISION={}",
        revision.trim()
    );
}
