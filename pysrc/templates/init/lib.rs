#![cfg_attr(not(feature = "std"), no_std)]

#[eosio_chain::contract]
#[allow(dead_code)]
mod {{name}} {
    use eosio_chain::{
        Name,
        eosio_println,
    };

    #[chain(table="counter")]
    pub struct Counter {
        #[chain(primary)]
        key: u64,
        count: u64
    }

    #[chain(main)]
    pub struct Contract {
        receiver: Name,
        first_receiver: Name,
        action: Name,
    }

    impl Contract {
        pub fn new(receiver: Name, first_receiver: Name, action: Name) -> Self {
            Self {
                receiver: receiver,
                first_receiver: first_receiver,
                action: action,
            }
        }

        #[chain(action = "inc")]
        pub fn inc_count(&self) {
            let db = Counter::new_table(self.receiver);
            let it = db.find(1u64);
            if let Some(mut value) = it.get_value() {
                value.count += 1;
                db.update(&it, &value, self.receiver);
                eosio_println!("count is", value.count);
            } else {
                db.store(&Counter{key: 1, count: 1}, self.receiver);
                eosio_println!("count is", 1);
            }
        }
    }
}

#[cfg(test)]
mod tests {

    use eosio_chain::ChainTester;
    use eosio_chain::serializer::Packer;
    use eosio_chain::eosio_chaintester;

    #[no_mangle]
    fn native_apply(receiver: u64, first_receiver: u64, action: u64) {
        crate::{{name}}::native_apply(receiver, first_receiver, action);
    }

    fn deploy_contract(tester: &mut ChainTester) {
        let package_name = env!("CARGO_PKG_NAME");
        eosio_chaintester::build_contract(&package_name, ".");

        let ref wasm_file = format!("./target/{package_name}.wasm");
        let ref abi_file = format!("./target/{package_name}.abi");
        tester.deploy_contract("hello", wasm_file, abi_file).unwrap();
    }

    fn update_auth(tester: &mut ChainTester) {
        let updateauth_args = r#"{
            "account": "hello",
            "permission": "active",
            "parent": "owner",
            "auth": {
                "threshold": 1,
                "keys": [
                    {
                        "key": "EOS6AjF6hvF7GSuSd4sCgfPKq5uWaXvGM2aQtEUCwmEHygQaqxBSV",
                        "weight": 1
                    }
                ],
                "accounts": [{"permission":{"actor": "hello", "permission": "eosio.code"}, "weight":1}],
                "waits": []
            }
        }"#;

        let permissions = r#"
        {
            "hello": "active"
        }
        "#;

        tester.push_action("eosio", "updateauth", updateauth_args.into(), permissions).unwrap();
        tester.produce_block();
    }

    #[test]
    fn test_inc() {
        let exe = std::env::current_exe();
        println!("{exe:?}");
    
        let mut tester = ChainTester::new();
        tester.enable_debug_contract("hello", true).unwrap();

        deploy_contract(&mut tester);
        update_auth(&mut tester);
    
        let permissions = r#"
        {
            "hello": "active"
        }
        "#;
        tester.push_action("hello", "inc", "".into(), permissions).unwrap();
        tester.produce_block();

        tester.push_action("hello", "inc", "".into(), permissions).unwrap();
        tester.produce_block();
    }
}
