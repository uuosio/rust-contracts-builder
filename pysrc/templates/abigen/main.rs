use std::{{fs, path::Path}};

extern crate contract;

fn main() -> Result<(), std::io::Error> {{
	let abi = contract::generate_abi();
	fs::write(Path::new("{target}/{package_name}.abi"), abi)?;
	Ok(())
}}
