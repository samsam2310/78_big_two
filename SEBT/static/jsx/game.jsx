(function(){
    console.log('init');
    var STYLE = '♣◆♥♠';
    var Card = React.createClass({
        render: function() {
            var card = this.props.card;
            var s = STYLE[parseInt(card[0])];
            var n = card[1]=='T'?'10':card[1];
            return (<span className={'card'}>{s}{n}</span>);
        }
    });
    var Table = React.createClass({
        render: function() {
            var cards = this.props.cards.map(function(v){
                return (<Card card={v}/>);
            });
            return (
                <div className={'current_card'}>
                    <span className={'current_card_title'}>Current Card</span>
                    <div className={'current_card_board'}>{cards}</div>
                </div>
            );
        }
    });
    var CountDown = React.createClass({
        getInitialState: function() {
            return {time: 0};
        },
        componentDidMount: function(nprop){
            this._mount = true;
            this.updateTime();
        },
        componentWillUnmount: function(){
            this._mount = false;
        },
        getTime: function(){
            var local = new Date().getTime()/1000;
            return local + this.props.delay;
        },
        updateTime: function(){
            var time = this.props.deadline - this.getTime();
            if(time < 0)time = 0;
            this.setState({time: time});
            if(this._mount)setTimeout(this.updateTime, 50);
        },
        render: function() {
            var time = 'OK';
            if(this.props.deadline != 0)time = this.props.deadline - this.getTime();
            if(time < 0)time = 0;
            return (<span>{this.state.time.toFixed(1)}</span>);
        }
    });
    var Player = React.createClass({
        render: function() {
            var turn = (<span className={'not-turn'}>Not Turn</span>);
            if(this.props.turn_num == this.props.index)turn = <span className={'turn'}>Turn!</span>
            return (
                <div className={'player'}>
                    <span className={'player-name'}>{this.props.player['name']}</span>
                    <span className={'player-card'}>
                        <span className={'card_icon'}></span>
                        <span className={'card_num'}>{this.props.player['card']}</span>
                    </span>
                    <span className={Number(this.props.player['conn'])==1?'avail player-conn':'unavail player-conn'}>
                        {Number(this.props.player['conn'])==1?'Online':'Offline'}
                    </span>
                    {turn}
                    <CountDown delay={this.props.delay} deadline={this.props.player.deadline}/>
                </div>
            );
        }
    });
    var Control = React.createClass({
        getInitialState: function() {
            return {
                status: []
            };
        },
        componentWillReceiveProps: function(nxtProp) {
            if(nxtProp.cards && nxtProp.cards.length == this.props.cards.length){
                for(var i in nxtProp.cards){
                    if(this.props.cards[i] != nxtProp.cards[i]){
                        this.setState({status: []});
                        return;
                    }
                }
            }
        },
        handleTrow: function(type){
            console.log('handle '+type);
            var ch_cs = [];
            for(var i in this.props.cards){
                if(this.state.status[i])ch_cs.push(this.props.cards[i])
            }
            this.props.onClick({type: type, card: ch_cs});
        },
        createBtn: function(is_ok, name, type, className) {
            if(is_ok){
                var that = this;
                return (<button className={className}
                    onClick={function(){that.props.onClick({'type':type})}}>{name}</button>);
            }
            return null;
        },
        render: function() {
            var that = this;
            var ch_c = this.props.cards.map(function(v, i){
                if(that.state.status[i]){
                    return (<Card card={v}/>);
                }
                return (<span/>);
            });
            var card = this.props.cards.map(function(v, i){
                var click = function(){
                    var status = that.state.status.slice();
                    status[i] = !status[i];
                    that.setState({status: status});
                }
                return (<button onClick={click}><Card card={v}/></button>);
            });
            var start_btn = this.createBtn(this.props.start_btn, '開始', 'start', 'btn btn-success btn-start');
            var reset_btn = this.createBtn(this.props.reset_btn, '重設', 'reset', 'btn btn-danger btn-reset');
            var signin_btn = this.createBtn(this.props.signin_btn, '參加', 'signin', 'btn btn-danger');
            var signout_btn = this.createBtn(this.props.signout_btn, '觀戰', 'signout', 'btn btn-danger');
            return (
                <div>
                    <h4 className={'name'}>{this.props.name}</h4>
                    <div className={'user_card'}>{ch_c}</div>
                    <div className={'user_card_set'}>{card}</div>
                    <div>
                      <div className={'form-inline'}>
                        <div className={'form-group'}>{signin_btn}</div>
                        <div className={'form-group'}>{signout_btn}</div>
                        <div className={'form-group'}>{start_btn}</div>
                        <div className={'form-group'}>{reset_btn}</div>
                        <div className={'form-group'}><button className={'btn btn-info btn-change'} disabled={!this.props.is_your_turn} onClick={function(){that.handleTrow('change')}}>換牌</button></div>
                        <div className={'form-group'}><button className={'btn btn-info btn-throw'} disabled={!this.props.is_your_turn} onClick={function(){that.handleTrow('throw')}}>出牌</button></div>
                        <div className={'form-group'}><button className={'btn btn-info btn-pick'} disabled={!this.props.is_your_turn} onClick={function(){that.props.onClick({'type':'pick'})}}>抽牌</button></div>
                      </div>
                    </div>
                </div>
            );
        }
    });
    var GameTable = React.createClass({
        getInitialState: function() {
            return {
                status: '?',
                your_name: 'Name',
                your_card: ['0A','4K'],
                current_card: ['3K','2K'],
                turn: '',
                turn_num: -1,
                players: [{name: 'a', card: 2},{name: 'b', card: 2}],
                room_manager: 'Manager',
                online_user: 0,
                delay: 0,
            };
        },
        componentDidMount: function() {
            var url = 'ws://' + window.location.host + '/gamesocket'
            var conn = new WebSocket(url);
            this.send = function(json) {
                conn.send(JSON.stringify(json));
            };
            this.socketState = function(){
                return conn.readyState;
            };
            var that = this;
            conn.onmessage = function(evt) {
                var json = JSON.parse(evt.data);
                that.handleMessage(json);
            };
            setTimeout(this.syncTime, 1000);
        },
        syncTime: function(){
            var state = this.socketState();
            if(state == 1)this.send({'req': 'synctime', 'time': new Date().getTime()/1000});
            if(state <= 1)setTimeout(this.syncTime, 10000);
        },
        handleMessage: function(json) {
            if(json.$set){
                console.log("Set!!!");
                console.log(json);
                this.setState(json.$set);
            }
        },
        handleClick: function(cli) {
            console.log(cli.type);
            if(cli.type=='throw' || cli.type=='change'){
                this.send({'req': cli.type, card: cli.card});
            }else{
                this.send({'req': cli.type});
            }
        },
        render: function() {
            var that = this;
            var players = this.state.players.map(function(v, i){
                return (<Player index={i} player={v} turn_num={that.state.turn_num} delay={that.state.delay}/>);
            });
            return (<div className={'thegame'}>
                <div className={'status'}><span className={'attr_title'}>Status</span>{this.state.status}</div>
                <Table cards={this.state.current_card}/>
                <div className={'gametable'}>
                {players}
                </div>
                <Control name={this.state.your_name}
                    cards={this.state.your_card}
                    start_btn={this.state.your_name==this.state.room_manager && this.state.status=='init'}
                    reset_btn={this.state.your_name==this.state.room_manager && this.state.status=='gameover'}
                    signin_btn={this.state.status=='init'&&this.state.your_status=='watching'}
                    signout_btn={this.state.status=='init'&&this.state.your_status=='init'}
                    onClick={this.handleClick}
                    is_your_turn={this.state.turn==this.state.your_name}/>
            </div>);
        }
    });
    ReactDOM.render(
        <GameTable />,
        document.getElementById('groot')
    );
    console.log('init-end');
}())
