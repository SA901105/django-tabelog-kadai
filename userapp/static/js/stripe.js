/*
    ビューにリクエストを送信して、Djangoサーバー側でStripeのセッションを作成し、
    そのセッションを基にStripeに対してクエリを送信します。
*/

// Stripeの公開可能キーを取得
fetch("/subscription/config/")
    // 結果オブジェクトを取得
    .then((result) => { return result.json(); })
    // データオブジェクトを取得
    .then((data) => {
        // Stripe.jsを初期化
        const stripe = Stripe(data.publicKey);

        // イベントハンドラ
        let submitBtn = document.querySelector("#checkout");
        if (submitBtn !== null) {
            // submitボタンがクリックされたとき
            submitBtn.addEventListener("click", () => {
                // カード名義情報を取得
                const cardholderFirstName = document.getElementById('cardholder-first-name').value;
                const cardholderLastName = document.getElementById('cardholder-last-name').value;
                const cardholderName = `${cardholderFirstName} ${cardholderLastName}`;

                // CSRFトークンを取得するためのinput要素を確認
                const csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
                
                // CSRFトークンが存在するか確認
                if (!csrfTokenInput) {
                    console.error("CSRFトークンが見つかりません。");
                    return;
                }

                // CSRFトークンを取得
                const csrfToken = csrfTokenInput.value;

                // Checkoutセッションを作成し、Stripe Checkoutにリダイレクト
                fetch("/subscription/create-checkout-session/", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken // ヘッダーにCSRFトークンを含める
                    },
                    body: JSON.stringify({
                        name: cardholderName  // 名義情報をリクエストボディに含める
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.sessionId) {
                        // Stripe Checkoutにリダイレクト
                        return stripe.redirectToCheckout({ sessionId: data.sessionId });
                    } else {
                        const message = 'セッションIDが返されませんでした'; 
                        document.getElementById('stripe-error').innerHTML = message;
                        console.error(message, data);
                    }
                })
                .catch(error => {
                    const message = '正しく処理が行えませんでした'; // エラーメッセージ内容
                    document.getElementById('stripe-error').innerHTML = message;
                    console.error(message, error);
                });
            });
        }
    })
    // エラーハンドリング
    .catch(error => {
        const message = '正しく処理が行えませんでした'; // エラーメッセージ内容
        document.getElementById('stripe-error').innerHTML = message;
        console.error(message, error);
    });
